#ifndef PACKAGE_H
#define PACKAGE_H

#include <string>

struct Package
{
    std::string name;

    std::string version;

    std::string author;

    std::string description;

    std::string repository;
};

#endif