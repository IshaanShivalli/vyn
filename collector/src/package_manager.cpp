#include "package_manager.h"
#include <iostream>

bool PackageManager::install(const std::string& name)
{
    std::cout << "Installing package: " << name << '\n';
    return true;
}

bool PackageManager::remove(const std::string& name)
{
    std::cout << "Removing package: " << name << '\n';
    return true;
}

bool PackageManager::update(const std::string& name)
{
    std::cout << "Updating package: " << name << '\n';
    return true;
}

bool PackageManager::updateAll()
{
    std::cout << "Updating all packages\n";
    return true;
}

bool PackageManager::show(const std::string& name)
{
    std::cout << "Showing package: " << name << '\n';
    return true;
}

bool PackageManager::search(const std::string& name)
{
    std::cout << "Searching package: " << name << '\n';
    return true;
}

bool PackageManager::publish(const std::string& name)
{
    std::cout << "Publishing package: " << name << '\n';
    return true;
}