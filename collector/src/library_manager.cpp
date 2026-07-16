#include "library_manager.h"
#include "downloader.h"

#include <algorithm>
#include <filesystem>
#include <iostream>
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
        std::filesystem::create_directories(sibling / "lib");
        return sibling;
    }

    std::string library_file(const std::string& name)
    {
        if (name.size() >= 3 && name.substr(name.size() - 3) == ".py")
            return name;
        return name + ".py";
    }
}

bool LibraryManager::install(const std::string& name)
{
    std::string file = library_file(name);
    std::filesystem::path dest = find_vyn_lib_root() / "lib" / file;
    std::string url = kBaseUrl + "/lib/" + file;

    Downloader downloader;
    bool ok = downloader.download(url, dest.string());
    std::cout << (ok ? "Installed library: " : "Failed to install library: ") << file << '\n';
    return ok;
}

bool LibraryManager::remove(const std::string& name)
{
    std::filesystem::path dest = find_vyn_lib_root() / "lib" / library_file(name);
    bool ok = std::filesystem::remove(dest);
    std::cout << (ok ? "Removed library: " : "Library not found: ") << library_file(name) << '\n';
    return ok;
}

bool LibraryManager::update(const std::string& name)
{
    return install(name);
}

bool LibraryManager::updateAll()
{
    bool ok = true;
    for (const std::string& name : {"crypto", "datetime", "encode", "json", "random", "re", "time", "token", "uuid"})
        ok = install(name) && ok;
    return ok;
}

bool LibraryManager::show(const std::string& name)
{
    std::string file = library_file(name);
    std::filesystem::path dest = find_vyn_lib_root() / "lib" / file;
    std::cout << "Library : " << name << '\n';
    std::cout << "File    : " << file << '\n';
    std::cout << "Status  : " << (std::filesystem::exists(dest) ? "Installed" : "Not installed") << '\n';
    return true;
}

bool LibraryManager::search(const std::string& name)
{
    std::string needle = name;
    std::transform(needle.begin(), needle.end(), needle.begin(), ::tolower);
    bool found = false;
    for (std::string lib : {"crypto", "datetime", "encode", "json", "random", "re", "time", "token", "uuid"})
    {
        std::string lower = lib;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
        if (lower.find(needle) != std::string::npos)
        {
            std::cout << lib << '\n';
            found = true;
        }
    }
    if (!found)
        std::cout << "No libraries found for: " << name << '\n';
    return found;
}
