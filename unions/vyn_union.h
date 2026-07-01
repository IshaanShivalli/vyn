#ifndef VYN_UNION_H
#define VYN_UNION_H

int vyn_union_define(const char *name, const char **field_names,
                     const int *field_types, int field_count);
int vyn_union_exists(const char *name);
int vyn_union_sizeof(const char *name);
int vyn_union_alloc(const char *union_name);
int vyn_union_free(int handle);
const char *vyn_union_instance_type(int handle);
int vyn_union_get_field(int handle, const char *field_name, void *out_buf);
int vyn_union_set_field(int handle, const char *field_name, const void *in_buf);
int vyn_union_get_int(int handle, const char *field_name, long *out);
int vyn_union_set_int(int handle, const char *field_name, long value);
int vyn_union_get_float(int handle, const char *field_name, double *out);
int vyn_union_set_float(int handle, const char *field_name, double value);

#endif
