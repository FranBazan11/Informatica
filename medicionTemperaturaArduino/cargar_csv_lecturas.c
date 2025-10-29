// =============================================================
// Analizador estadístico de lecturas de temperatura (CSV)
// -------------------------------------------------------------
// Lee "timestamp,tendencia,temperatura_C" y calcula:
// - Cantidad de lecturas
// - Mínimo y máximo (con fecha/hora)
// - Media, mediana, moda
// - Desviación estándar (muestral)
// =============================================================

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <math.h>

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
        if (strcmp(c1, "FechaHora") == 0) { free(buf); return 2; } // cabecera
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
    while (fgets(linea, sizeof(linea), f)) {
        char *ts = NULL; char tend = 'N'; double temp = 0.0;
        int ok = parse_line(linea, &ts, &tend, &temp);
        if (ok == 1) {
            if (!vec_push(v, ts, tend, temp)) { free(ts); fclose(f); return 0; }
            free(ts);
        }
    }
    fclose(f);
    return 1;
}

/*------------------ Estadísticas ----------------*/
static int cmp_temp(const void *a, const void *b) {
    double x = ((Lectura*)a)->temp - ((Lectura*)b)->temp;
    return (x < 0) ? -1 : (x > 0);
}

static double media(VectorLecturas *v) {
    long double sum = 0;
    for (size_t i = 0; i < v->size; i++) sum += v->data[i].temp;
    return (double)(sum / v->size);
}

static double mediana(VectorLecturas *v) {
    qsort(v->data, v->size, sizeof(Lectura), cmp_temp);
    if (v->size % 2)
        return v->data[v->size/2].temp;
    else
        return (v->data[v->size/2 - 1].temp + v->data[v->size/2].temp) / 2.0;
}

static double moda(VectorLecturas *v) {
    if (v->size == 0) return NAN;
    qsort(v->data, v->size, sizeof(Lectura), cmp_temp);
    double best = v->data[0].temp, last = v->data[0].temp;
    size_t best_cnt = 1, cnt = 1;
    for (size_t i = 1; i < v->size; i++) {
        if (fabs(v->data[i].temp - last) < 1e-6)
            cnt++;
        else {
            if (cnt > best_cnt) { best_cnt = cnt; best = last; }
            last = v->data[i].temp; cnt = 1;
        }
    }
    if (cnt > best_cnt) best = last;
    return best;
}

static double desviacion_estandar(VectorLecturas *v, double mean) {
    if (v->size < 2) return NAN;
    long double sum = 0;
    for (size_t i = 0; i < v->size; i++) {
        long double diff = v->data[i].temp - mean;
        sum += diff * diff;
    }
    return sqrt((double)(sum / (v->size - 1))); // muestral
}

/*-------------------- MAIN ----------------------*/
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: %s /ruta/al/registro.csv\n", argv[0]);
        return 1;
    }

    VectorLecturas v; vec_init(&v);

    if (!cargar_csv(argv[1], &v)) {
        vec_free(&v);
        return 1;
    }

    if (v.size == 0) {
        printf("El archivo no contiene lecturas válidas.\n");
        vec_free(&v);
        return 0;
    }

    // --- Mínimo y máximo ---
    double min = v.data[0].temp, max = v.data[0].temp;
    char *tmin = v.data[0].timestamp, *tmax = v.data[0].timestamp;
    for (size_t i = 1; i < v.size; i++) {
        if (v.data[i].temp < min) { min = v.data[i].temp; tmin = v.data[i].timestamp; }
        if (v.data[i].temp > max) { max = v.data[i].temp; tmax = v.data[i].timestamp; }
    }

    double mean = media(&v);
    double med = mediana(&v);
    double mode = moda(&v);
    double std = desviacion_estandar(&v, mean);

    printf("=========================================\n");
    printf("Archivo: %s\n", argv[1]);
    printf("Cantidad de lecturas: %zu\n", v.size);
    printf("-----------------------------------------\n");
    printf("Temperatura mínima: %.2f °C (%s)\n", min, tmin);
    printf("Temperatura máxima: %.2f °C (%s)\n", max, tmax);
    printf("Media: %.2f °C\n", mean);
    printf("Mediana: %.2f °C\n", med);
    printf("Moda: %.2f °C\n", mode);
    printf("Desviación estándar (muestral): %.2f °C\n", std);
    printf("=========================================\n");

    printf("\nJustificación:\n");
    printf("Se utiliza la desviación estándar muestral porque:\n");
    printf("- Las lecturas provienen de una muestra del sistema (no de toda la población posible).\n");
    printf("- Mide la dispersión en las mismas unidades (°C), facilitando interpretación.\n");
    printf("- Es apropiada cuando las mediciones son aproximadamente normales\n");
    printf("  y no se esperan valores atípicos extremos.\n");

    vec_free(&v);
    return 0;
}