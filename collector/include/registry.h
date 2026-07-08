#ifndef REGISTRY_H
#define REGISTRY_H

#include <string>

class Registry
{
public:

    bool update();

    bool packageExists(const std::string&);

    bool libraryExists(const std::string&);

    std::string latestVersion(const std::string&);
};

#endif