#ifndef VYN_STRUCT_H
#define VYN_STRUCT_H

#include <stddef.h>

#define VYN_MAX_FIELDS 32
#define VYN_MAX_NAME   64
#define VYN_MAX_STRUCTS 128
#define VYN_MAX_INSTANCES 1024

typedef enum {
    VYN_TYPE_INT,
    VYN_TYPE_FLOAT,
    VYN_TYPE_CHAR,
    VYN_TYPE_BOOL,
    VYN_TYPE_PTR
} VynFieldType;

typedef struct {
    char name[VYN_MAX_NAME];
    VynFieldType type;
    size_t offset;
    size_t size;
} VynFieldDef;

typedef struct {
    char name[VYN_MAX_NAME];
    VynFieldDef fields[VYN_MAX_FIELDS];
    int field_count;
    size_t total_size;
    int is_union;
} VynStructDef;

/* Registers a struct or union shape. Returns 0 on success, -1 on failure
   (e.g. registry full, name too long, too many fields). */
int vyn_struct_define(const char *name, const char **field_names,
                       const int *field_types, int field_count, int is_union);

/* Allocates a zeroed instance of a previously defined struct/union.
   Returns a positive handle ID, or -1 if the struct name is unknown
   or the instance table is full. */
int vyn_struct_alloc(const char *struct_name);

/* Frees an instance by handle. Returns 0 on success, -1 if handle invalid. */
int vyn_struct_free(int handle);

/* Field access. get_field writes the raw bytes into out_buf (caller must
   size it appropriately, max 8 bytes for current types). Returns field
   size in bytes, or -1 on error (bad handle / unknown field). */
int vyn_struct_get_field(int handle, const char *field_name, void *out_buf);

/* Sets a field's value from raw bytes pointed to by in_buf.
   Returns 0 on success, -1 on error. */
int vyn_struct_set_field(int handle, const char *field_name, const void *in_buf);

/* Convenience typed accessors */
int vyn_struct_get_int(int handle, const char *field_name, long *out);
int vyn_struct_set_int(int handle, const char *field_name, long value);

int vyn_struct_get_float(int handle, const char *field_name, double *out);
int vyn_struct_set_float(int handle, const char *field_name, double value);

/* Returns the struct name an instance belongs to, or NULL if invalid. */
const char *vyn_struct_instance_type(int handle);

/* Returns 1 if a struct/union with this name is registered, else 0. */
int vyn_struct_exists(const char *name);

/* Returns the size in bytes of a registered struct/union, or -1 if unknown. */
int vyn_struct_sizeof(const char *name);

#endif /* VYN_STRUCT_H */