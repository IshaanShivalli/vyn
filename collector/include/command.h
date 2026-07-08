#ifndef COMMAND_H
#define COMMAND_H

enum class Command
{
    INSTALL,
    DELETE,
    UPDATE,
    SHOW,
    SEARCH,
    LIST,
    PUBLISH,
    UNKNOWN
};

enum class Target
{
    PACKAGE,
    LIBRARY,
    ALL,
    NONE
};

#endif