// cargar_csv_lecturas.c
// Lee "timestamp,tendencia,temperatura_C" y guarda en memoria dinámica.
// Compilar:  gcc -std=c11 -O2 cargar_csv_lecturas.c -o cargar_csv_lecturas
// Ejecutar:  ./cargar_csv_lecturas /ruta/al/registro.csv

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>

typedef struct {
    char *timestamp;  // copia dinámica del timestamp
    char tendencia;   // 'A','B','M','N'
    double temp;      // °C
} Lectura;

typedef struct {
    Lectura *data;
    size_t size;
    size_t capacity;
} VectorLecturas;

/*------------------ Utilidades ------------------*/
static void chomp(char *s) {
    if (!s) return;
    size_t n = strlen(s);
    while (n && (s[n-1] == '\n' || s[n-1] == '\r')) s[--n] = '\0';
}
static void trim(char *s) {
    if (!s) return;
    size_t i = 0;
    while (s[i] && isspace((unsigned char)s[i])) i++;
    if (i) memmove(s, s + i, strlen(s + i) + 1);
    size_t n = strlen(s);
    while (n && isspace((unsigned char)s[n-1])) s[--n] = '\0';
}

/*---------------- Vector dinámico ---------------*/
static void vec_init(VectorLecturas *v) {
    v->data = NULL; v->size = 0; v->capacity = 0;
}
static void vec_free(VectorLecturas *v) {
    if (!v) return;
    for (size_t i = 0; i < v->size; ++i) free(v->data[i].timestamp);
    free(v->data);
    v->data = NULL; v->size = v->capacity = 0;
}
static int vec_reserve(VectorLecturas *v, size_t need) {
    if (need <= v->capacity) return 1;
    size_t cap = v->capacity ? v->capacity * 2 : 16;
    if (cap < need) cap = need;
    void *p = realloc(v->data, cap * sizeof(Lectura));
    if (!p) return 0;
    v->data = (Lectura*)p; v->capacity = cap;
    return 1;
}
static int vec_push(VectorLecturas *v, const char *timestamp, char tendencia, double temp) {
    if (!vec_reserve(v, v->size + 1)) return 0;
    char *ts = strdup(timestamp ? timestamp : "");
    if (!ts) return 0;
    v->data[v->size].timestamp = ts;
    v->data[v->size].tendencia = tendencia;
    v->data[v->size].temp = temp;
    v->size++;
    return 1;
}

/*----------------- Parseo CSV -------------------*/
static int parse_line(const char *line, char **out_ts, char *out_tend, double *out_temp) {
    // Esperado: timestamp,tendencia,temperatura_C
    char *buf = strdup(line);
    if (!buf) return 0;
    chomp(buf); trim(buf);

    int ok = 0;
    char *save = NULL;
    char *c1 = strtok_r(buf, ",", &save);
    char *c2 = strtok_r(NULL, ",", &save);
    char *c3 = strtok_r(NULL, ",", &save);

    if (c1 && c2 && c3) {
        trim(c1); trim(c2); trim(c3);
        char tchar = c2[0] ? c2[0] : 'N';

        errno = 0;
        char *endp = NULL;
        double t = strtod(c3, &endp);
        if (errno == 0 && endp && (*endp == '\0' || isspace((unsigned char)*endp))) {
            *out_ts = strdup(c1);
            if (!*out_ts) { free(buf); return 0; }
            *out_tend = tchar;
            *out_temp = t;
            ok = 1;
        }
    }
    free(buf);
    return ok;
}

static int cargar_csv(const char *ruta, VectorLecturas *v) {
    FILE *f = fopen(ruta, "r");
    if (!f) {
        fprintf(stderr, "No se pudo abrir '%s': %s\n", ruta, strerror(errno));
        return 0;
    }
    char linea[1024];
    int first = 1;
    while (fgets(linea, sizeof(linea), f)) {
        if (first) { // saltear encabezado si existe
            first = 0;
            if (strstr(linea, "timestamp")) continue;
        }
        char *ts = NULL; char tend = 'N'; double temp = 0.0;
        if (!parse_line(linea, &ts, &tend, &temp)) {
            continue; // línea inválida -> ignorar
        }
        if (!vec_push(v, ts, tend, temp)) { free(ts); fclose(f); return 0; }
        free(ts); // ya se copió dentro del vector
    }
    fclose(f);
    return 1;
}

/*-------------------- Demo ----------------------*/
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: %s /ruta/al/registro.csv\n", argv[0]);
        return 1;
    }

    VectorLecturas lects; vec_init(&lects);

    if (!cargar_csv(argv[1], &lects)) {
        vec_free(&lects);
        return 1;
    }

    printf("Se cargaron %zu lecturas.\n", lects.size);

    // Ejemplo: acceder a los datos “sueltos” ya guardados en memoria dinámica
    // (acá solo imprimimos las primeras 5 para mostrar cómo se accede)
    size_t mostrar = lects.size < 5 ? lects.size : 5;
    for (size_t i = 0; i < mostrar; ++i) {
        printf("[%zu] timestamp=%s  tendencia=%c  temp=%.3f C\n",
               i, lects.data[i].timestamp, lects.data[i].tendencia, lects.data[i].temp);
    }

    // A partir de acá podés calcular estadísticas, etc., usando lects.data[i].temp, etc.

    vec_free(&lects);
    return 0;
}