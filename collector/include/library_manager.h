#ifndef LIBRARY_MANAGER_H
#define LIBRARY_MANAGER_H

#include <string>

class LibraryManager
{
public:

    bool install(const std::string&);

    bool remove(const std::string&);

    bool update(const std::string&);

    bool updateAll();

    bool show(const std::string&);

    bool search(const std::string&);
};

#endif