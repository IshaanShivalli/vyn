#include "library_manager.h"
#include <iostream>

bool LibraryManager::install(const std::string& name)
{
    std::cout << "Installing library: " << name << '\n';
    return true;
}

bool LibraryManager::remove(const std::string& name)
{
    std::cout << "Removing library: " << name << '\n';
    return true;
}

bool LibraryManager::update(const std::string& name)
{
    std::cout << "Updating library: " << name << '\n';
    return true;
}

bool LibraryManager::updateAll()
{
    std::cout << "Updating all libraries\n";
    return true;
}

bool LibraryManager::show(const std::string& name)
{
    std::cout << "Showing library: " << name << '\n';
    return true;
}

bool LibraryManager::search(const std::string& name)
{
    std::cout << "Searching library: " << name << '\n';
    return true;
}