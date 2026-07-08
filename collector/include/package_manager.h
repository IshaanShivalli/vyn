#ifndef PACKAGE_MANAGER_H
#define PACKAGE_MANAGER_H

#include <string>

class PackageManager
{
public:

    bool install(const std::string&);

    bool remove(const std::string&);

    bool update(const std::string&);

    bool updateAll();

    bool show(const std::string&);

    bool search(const std::string&);

    bool publish(const std::string&);
};

#endif