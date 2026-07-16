#include "package_manager.h"
#include "downloader.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

namespace
{
    const std::string kBaseUrl = "https://raw.githubusercontent.com/IshaanShivalli/vyn-lib/main";

    std::filesystem::path find_vyn_root()
    {
        std::filesystem::path current = std::filesystem::current_path();
        for (int i = 0; i < 4; ++i)
        {
            if (std::filesystem::exists(current / "main.py"))
                return current;
            if (!current.has_parent_path())
                break;
            current = current.parent_path();
        }
        return std::filesystem::current_path();
    }

    std::filesystem::path find_vyn_lib_root()
    {
        std::filesystem::path root = find_vyn_root();
        std::filesystem::path sibling = root.parent_path() / "vyn-lib";
        if (std::filesystem::exists(sibling))
            return sibling;
        std::filesystem::create_directories(sibling / "packages");
        return sibling;
    }

    std::filesystem::path collector_root()
    {
        std::filesystem::path root = find_vyn_root();
        if (std::filesystem::exists(root / "collector" / "registry" / "packages.json"))
            return root / "collector";
        return std::filesystem::current_path() / "collector";
    }

    std::string package_file(const std::string& name)
    {
        if (name.size() >= 4 && name.substr(name.size() - 4) == ".vyn")
            return name;
        return name + ".vyn";
    }

    std::string read_packages_registry()
    {
        std::ifstream in(collector_root() / "registry" / "packages.json");
        std::ostringstream ss;
        ss << in.rdbuf();
        return ss.str();
    }
}

bool PackageManager::install(const std::string& name)
{
    std::string file = package_file(name);
    std::filesystem::path dest = find_vyn_lib_root() / "packages" / file;
    std::string url = kBaseUrl + "/packages/" + file;

    Downloader downloader;
    bool ok = downloader.download(url, dest.string());
    std::cout << (ok ? "Installed package: " : "Failed to install package: ") << file << '\n';
    return ok;
}

bool PackageManager::remove(const std::string& name)
{
    std::filesystem::path dest = find_vyn_lib_root() / "packages" / package_file(name);
    bool ok = std::filesystem::remove(dest);
    std::cout << (ok ? "Removed package: " : "Package not found: ") << package_file(name) << '\n';
    return ok;
}

bool PackageManager::update(const std::string& name)
{
    return install(name);
}

bool PackageManager::updateAll()
{
    bool ok = true;
    for (const std::string& name : {"Logger", "Primes", "Search", "Sort", "StringUtils", "Validation"})
        ok = install(name) && ok;
    return ok;
}

bool PackageManager::show(const std::string& name)
{
    std::string registry = read_packages_registry();
    std::filesystem::path dest = find_vyn_lib_root() / "packages" / package_file(name);
    std::cout << "Package : " << name << '\n';
    std::cout << "File    : " << package_file(name) << '\n';
    std::cout << "Status  : " << (std::filesystem::exists(dest) ? "Installed" : "Not installed") << '\n';
    if (registry.find("\"" + name + "\"") != std::string::npos)
        std::cout << "Registry: Listed\n";
    else
        std::cout << "Registry: Not listed locally\n";
    return true;
}

bool PackageManager::search(const std::string& name)
{
    std::string registry = read_packages_registry();
    std::string needle = name;
    std::transform(needle.begin(), needle.end(), needle.begin(), ::tolower);
    bool found = false;

    for (const std::string& pack : {"Logger", "Primes", "Search", "Sort", "StringUtils", "Validation"})
    {
        std::string lower = pack;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
        if (lower.find(needle) != std::string::npos || registry.find("\"" + pack + "\"") != std::string::npos && needle.empty())
        {
            std::cout << pack << '\n';
            found = true;
        }
    }
    if (!found)
        std::cout << "No packages found for: " << name << '\n';
    return found;
}

bool PackageManager::publish(const std::string& name)
{
    std::cout << "Publishing package: " << name << '\n';
    return true;
}
