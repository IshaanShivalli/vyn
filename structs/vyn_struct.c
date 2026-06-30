#include "vyn_struct.h"
#include <string.h>
#include <stdlib.h>

static VynStructDef g_struct_defs[VYN_MAX_STRUCTS];
static int g_struct_def_count = 0;

typedef struct {
    int in_use;
    int def_index;   /* index into g_struct_defs */
    void *data;      /* raw allocated bytes */
} VynInstance;

static VynInstance g_instances[VYN_MAX_INSTANCES];

static size_t type_size(VynFieldType t) {
    switch (t) {
        case VYN_TYPE_INT:   return sizeof(long);
        case VYN_TYPE_FLOAT: return sizeof(double);
        case VYN_TYPE_CHAR:  return sizeof(char);
        case VYN_TYPE_BOOL:  return sizeof(char);
        case VYN_TYPE_PTR:   return sizeof(void *);
        default:             return 0;
    }
}

static size_t align_up(size_t offset, size_t alignment) {
    if (alignment == 0) return offset;
    size_t rem = offset % alignment;
    if (rem == 0) return offset;
    return offset + (alignment - rem);
}

static int find_struct_def(const char *name) {
    for (int i = 0; i < g_struct_def_count; i++) {
        if (strncmp(g_struct_defs[i].name, name, VYN_MAX_NAME) == 0) {
            return i;
        }
    }
    return -1;
}

int vyn_struct_define(const char *name, const char **field_names,
                       const int *field_types, int field_count, int is_union) {
    if (!name || field_count <= 0 || field_count > VYN_MAX_FIELDS) return -1;
    if (strlen(name) >= VYN_MAX_NAME) return -1;
    if (g_struct_def_count >= VYN_MAX_STRUCTS) return -1;
    if (find_struct_def(name) != -1) return -1; /* already defined */

    VynStructDef *def = &g_struct_defs[g_struct_def_count];
    memset(def, 0, sizeof(VynStructDef));
    strncpy(def->name, name, VYN_MAX_NAME - 1);
    def->field_count = field_count;
    def->is_union = is_union;

    size_t running_offset = 0;
    size_t max_field_size = 0;

    for (int i = 0; i < field_count; i++) {
        if (strlen(field_names[i]) >= VYN_MAX_NAME) return -1;

        VynFieldDef *f = &def->fields[i];
        strncpy(f->name, field_names[i], VYN_MAX_NAME - 1);
        f->type = (VynFieldType)field_types[i];
        f->size = type_size(f->type);
        if (f->size == 0) return -1; /* unknown type */

        if (is_union) {
            f->offset = 0;
            if (f->size > max_field_size) max_field_size = f->size;
        } else {
            running_offset = align_up(running_offset, f->size);
            f->offset = running_offset;
            running_offset += f->size;
        }
    }

    def->total_size = is_union ? max_field_size : running_offset;
    /* round struct size up to largest alignment for array-friendliness */
    if (!is_union && def->total_size > 0) {
        size_t align = 1;
        for (int i = 0; i < field_count; i++) {
            if (def->fields[i].size > align) align = def->fields[i].size;
        }
        def->total_size = align_up(def->total_size, align);
    }

    g_struct_def_count++;
    return 0;
}

int vyn_struct_exists(const char *name) {
    return find_struct_def(name) != -1;
}

int vyn_struct_sizeof(const char *name) {
    int idx = find_struct_def(name);
    if (idx == -1) return -1;
    return (int)g_struct_defs[idx].total_size;
}

static int find_free_instance_slot(void) {
    for (int i = 0; i < VYN_MAX_INSTANCES; i++) {
        if (!g_instances[i].in_use) return i;
    }
    return -1;
}

int vyn_struct_alloc(const char *struct_name) {
    int def_idx = find_struct_def(struct_name);
    if (def_idx == -1) return -1;

    int slot = find_free_instance_slot();
    if (slot == -1) return -1;

    size_t size = g_struct_defs[def_idx].total_size;
    void *data = calloc(1, size > 0 ? size : 1);
    if (!data) return -1;

    g_instances[slot].in_use = 1;
    g_instances[slot].def_index = def_idx;
    g_instances[slot].data = data;

    /* handles are 1-indexed so 0/-1 can mean "invalid" */
    return slot + 1;
}

static VynInstance *resolve_instance(int handle) {
    int idx = handle - 1;
    if (idx < 0 || idx >= VYN_MAX_INSTANCES) return NULL;
    if (!g_instances[idx].in_use) return NULL;
    return &g_instances[idx];
}

int vyn_struct_free(int handle) {
    VynInstance *inst = resolve_instance(handle);
    if (!inst) return -1;
    free(inst->data);
    inst->data = NULL;
    inst->in_use = 0;
    inst->def_index = -1;
    return 0;
}

const char *vyn_struct_instance_type(int handle) {
    VynInstance *inst = resolve_instance(handle);
    if (!inst) return NULL;
    return g_struct_defs[inst->def_index].name;
}

static VynFieldDef *find_field(VynStructDef *def, const char *field_name) {
    for (int i = 0; i < def->field_count; i++) {
        if (strncmp(def->fields[i].name, field_name, VYN_MAX_NAME) == 0) {
            return &def->fields[i];
        }
    }
    return NULL;
}

int vyn_struct_get_field(int handle, const char *field_name, void *out_buf) {
    VynInstance *inst = resolve_instance(handle);
    if (!inst) return -1;
    VynStructDef *def = &g_struct_defs[inst->def_index];
    VynFieldDef *f = find_field(def, field_name);
    if (!f) return -1;

    memcpy(out_buf, (char *)inst->data + f->offset, f->size);
    return (int)f->size;
}

int vyn_struct_set_field(int handle, const char *field_name, const void *in_buf) {
    VynInstance *inst = resolve_instance(handle);
    if (!inst) return -1;
    VynStructDef *def = &g_struct_defs[inst->def_index];
    VynFieldDef *f = find_field(def, field_name);
    if (!f) return -1;

    memcpy((char *)inst->data + f->offset, in_buf, f->size);
    return 0;
}

int vyn_struct_get_int(int handle, const char *field_name, long *out) {
    return vyn_struct_get_field(handle, field_name, out) > 0 ? 0 : -1;
}

int vyn_struct_set_int(int handle, const char *field_name, long value) {
    return vyn_struct_set_field(handle, field_name, &value);
}

int vyn_struct_get_float(int handle, const char *field_name, double *out) {
    return vyn_struct_get_field(handle, field_name, out) > 0 ? 0 : -1;
}

int vyn_struct_set_float(int handle, const char *field_name, double value) {
    return vyn_struct_set_field(handle, field_name, &value);
}