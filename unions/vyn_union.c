#include <string.h>
#include <stdlib.h>

#define VYN_MAX_UNIONS 128
#define VYN_MAX_FIELDS 32
#define VYN_MAX_NAME 64
#define VYN_MAX_INSTANCES 256

typedef enum {
    VYN_TYPE_INT = 0,
    VYN_TYPE_FLOAT = 1,
    VYN_TYPE_CHAR = 2,
    VYN_TYPE_BOOL = 3,
    VYN_TYPE_PTR = 4
} VynFieldType;

typedef struct {
    char name[VYN_MAX_NAME];
    int field_count;
    struct {
        char name[VYN_MAX_NAME];
        VynFieldType type;
        size_t size;
        size_t offset;
    } fields[VYN_MAX_FIELDS];
    size_t total_size;
} VynUnionDef;

typedef struct {
    int in_use;
    int def_index;
    void *data;
} VynInstance;

static VynUnionDef g_union_defs[VYN_MAX_UNIONS];
static int g_union_def_count = 0;
static VynInstance g_instances[VYN_MAX_INSTANCES];

static size_t type_size(VynFieldType t) {
    switch (t) {
        case VYN_TYPE_INT: return sizeof(long);
        case VYN_TYPE_FLOAT: return sizeof(double);
        case VYN_TYPE_CHAR: return sizeof(char);
        case VYN_TYPE_BOOL: return sizeof(char);
        case VYN_TYPE_PTR: return sizeof(void *);
        default: return 0;
    }
}

static int find_union_def(const char *name) {
    for (int i = 0; i < g_union_def_count; i++) {
        if (strncmp(g_union_defs[i].name, name, VYN_MAX_NAME) == 0) {
            return i;
        }
    }
    return -1;
}

int vyn_union_define(const char *name, const char **field_names,
                     const int *field_types, int field_count) {
    if (!name || field_count <= 0 || field_count > VYN_MAX_FIELDS) return -1;
    if (strlen(name) >= VYN_MAX_NAME) return -1;
    if (g_union_def_count >= VYN_MAX_UNIONS) return -1;
    if (find_union_def(name) != -1) return -1;

    VynUnionDef *def = &g_union_defs[g_union_def_count];
    memset(def, 0, sizeof(VynUnionDef));
    strncpy(def->name, name, VYN_MAX_NAME - 1);
    def->field_count = field_count;

    size_t max_size = 0;
    for (int i = 0; i < field_count; i++) {
        if (strlen(field_names[i]) >= VYN_MAX_NAME) return -1;
        strncpy(def->fields[i].name, field_names[i], VYN_MAX_NAME - 1);
        def->fields[i].type = (VynFieldType)field_types[i];
        def->fields[i].size = type_size(def->fields[i].type);
        if (def->fields[i].size == 0) return -1;
        if (def->fields[i].size > max_size) max_size = def->fields[i].size;
        def->fields[i].offset = 0;
    }

    def->total_size = max_size;
    g_union_def_count++;
    return 0;
}

int vyn_union_exists(const char *name) {
    return find_union_def(name) != -1;
}

int vyn_union_sizeof(const char *name) {
    int idx = find_union_def(name);
    return idx == -1 ? -1 : (int)g_union_defs[idx].total_size;
}

static int find_free_instance_slot(void) {
    for (int i = 0; i < VYN_MAX_INSTANCES; i++) {
        if (!g_instances[i].in_use) return i;
    }
    return -1;
}

int vyn_union_alloc(const char *union_name) {
    int def_idx = find_union_def(union_name);
    if (def_idx == -1) return -1;
    int slot = find_free_instance_slot();
    if (slot == -1) return -1;
    size_t size = g_union_defs[def_idx].total_size;
    void *data = calloc(1, size > 0 ? size : 1);
    if (!data) return -1;
    g_instances[slot].in_use = 1;
    g_instances[slot].def_index = def_idx;
    g_instances[slot].data = data;
    return slot + 1;
}

int vyn_union_free(int handle) {
    if (handle <= 0 || handle - 1 >= VYN_MAX_INSTANCES) return -1;
    VynInstance *inst = &g_instances[handle - 1];
    if (!inst->in_use) return -1;
    free(inst->data);
    inst->data = NULL;
    inst->in_use = 0;
    inst->def_index = -1;
    return 0;
}

const char *vyn_union_instance_type(int handle) {
    if (handle <= 0 || handle - 1 >= VYN_MAX_INSTANCES) return NULL;
    VynInstance *inst = &g_instances[handle - 1];
    if (!inst->in_use) return NULL;
    return g_union_defs[inst->def_index].name;
}

static int find_field(VynUnionDef *def, const char *field_name) {
    for (int i = 0; i < def->field_count; i++) {
        if (strncmp(def->fields[i].name, field_name, VYN_MAX_NAME) == 0) {
            return i;
        }
    }
    return -1;
}

int vyn_union_get_field(int handle, const char *field_name, void *out_buf) {
    if (handle <= 0 || handle - 1 >= VYN_MAX_INSTANCES) return -1;
    VynInstance *inst = &g_instances[handle - 1];
    if (!inst->in_use) return -1;
    VynUnionDef *def = &g_union_defs[inst->def_index];
    int idx = find_field(def, field_name);
    if (idx == -1) return -1;
    memcpy(out_buf, (char *)inst->data + def->fields[idx].offset, def->fields[idx].size);
    return (int)def->fields[idx].size;
}

int vyn_union_set_field(int handle, const char *field_name, const void *in_buf) {
    if (handle <= 0 || handle - 1 >= VYN_MAX_INSTANCES) return -1;
    VynInstance *inst = &g_instances[handle - 1];
    if (!inst->in_use) return -1;
    VynUnionDef *def = &g_union_defs[inst->def_index];
    int idx = find_field(def, field_name);
    if (idx == -1) return -1;
    memcpy((char *)inst->data + def->fields[idx].offset, in_buf, def->fields[idx].size);
    return 0;
}

int vyn_union_get_int(int handle, const char *field_name, long *out) {
    return vyn_union_get_field(handle, field_name, out) > 0 ? 0 : -1;
}

int vyn_union_set_int(int handle, const char *field_name, long value) {
    return vyn_union_set_field(handle, field_name, &value);
}

int vyn_union_get_float(int handle, const char *field_name, double *out) {
    return vyn_union_get_field(handle, field_name, out) > 0 ? 0 : -1;
}

int vyn_union_set_float(int handle, const char *field_name, double value) {
    return vyn_union_set_field(handle, field_name, &value);
}
