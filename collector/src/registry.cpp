#include "registry.h"

bool Registry::update()
{
    return true;
}

bool Registry::packageExists(const std::string& name)
{
    return false;
}

bool Registry::libraryExists(const std::string& name)
{
    return false;
}

std::string Registry::latestVersion(const std::string& name)
{
    return "";
}