#include "cli.h"
#include "package_manager.h"
#include "library_manager.h"

#include <iostream>
#include <string>
#include <filesystem>
#include <vector>
#include <windows.h>
#include <urlmon.h>

void CLI::run(int argc, char* argv[])
{
    if (argc < 2)
    {
        std::cout << "Vyn Package Collector\n";
        return;
    }

    PackageManager packageManager;
    LibraryManager libraryManager;

    std::string cmd = argv[1];

    if (cmd == "*")
    {
        if (argc < 3 || std::string(argv[2]) != "install")
        {
            std::cout << "Usage: vyn-collector * install\n";
            return;
        }

        std::cout << "Setting up all libraries and packages...\n";
        
        std::string base_dir = ".";
        if (!std::filesystem::exists("main.py") && std::filesystem::exists("../main.py"))
        {
            base_dir = "..";
        }
        else if (!std::filesystem::exists("main.py") && std::filesystem::exists("../../main.py"))
        {
            base_dir = "../..";
        }
        
        std::string lib_path = base_dir + "/lib";
        std::string pack_path = base_dir + "/packages";
        
        std::cout << "Removing old directories: " << lib_path << " and " << pack_path << '\n';
        std::filesystem::remove_all(lib_path);
        std::filesystem::remove_all(pack_path);
        
        std::string dep_dir = base_dir + "/vyn-dependencies";
        std::string dep_lib = dep_dir + "/libraries";
        std::string dep_pack = dep_dir + "/packages";
        
        std::filesystem::create_directories(dep_lib);
        std::filesystem::create_directories(dep_pack);
        
        std::vector<std::string> libraries = {
            "crypto.py", "datetime.py", "encode.py", "json.py",
            "random.py", "re.py", "time.py", "token.py", "uuid.py"
        };
        
        std::cout << "Downloading libraries...\n";
        for (const auto& lib : libraries)
        {
            std::string url = "https://raw.githubusercontent.com/IshaanShivalli/vyn-lib/main/lib/" + lib;
            std::string dest = dep_lib + "/" + lib;
            std::cout << "  -> " << lib << "... ";
            HRESULT hr = URLDownloadToFileA(NULL, url.c_str(), dest.c_str(), 0, NULL);
            if (SUCCEEDED(hr))
                std::cout << "done\n";
            else
                std::cout << "failed\n";
        }
        
        std::vector<std::string> packages = {
            "Logger.vyn", "Primes.vyn", "Search.vyn", "Sort.vyn",
            "StringUtils.vyn", "Validation.vyn"
        };
        
        std::cout << "Downloading packages...\n";
        for (const auto& pack : packages)
        {
            std::string url = "https://raw.githubusercontent.com/IshaanShivalli/vyn-lib/main/packages/" + pack;
            std::string dest = dep_pack + "/" + pack;
            std::cout << "  -> " << pack << "... ";
            HRESULT hr = URLDownloadToFileA(NULL, url.c_str(), dest.c_str(), 0, NULL);
            if (SUCCEEDED(hr))
                std::cout << "done\n";
            else
                std::cout << "failed\n";
        }
        
        std::cout << "Setup complete.\n";
        return;
    }

    if (cmd == "-pack")
    {
        if (argc < 4) return;

        std::string action = argv[2];
        std::string name = argv[3];

        if (action == "install")
            packageManager.install(name);

        else if (action == "remove")
            packageManager.remove(name);

        else if (action == "show")
            packageManager.show(name);

        else if (action == "search")
            packageManager.search(name);

        else if (action == "publish")
            packageManager.publish(name);
    }

    else if (cmd == "-lib")
    {
        if (argc < 4) return;

        std::string action = argv[2];
        std::string name = argv[3];

        if (action == "install")
            libraryManager.install(name);

        else if (action == "remove")
            libraryManager.remove(name);

        else if (action == "show")
            libraryManager.show(name);

        else if (action == "search")
            libraryManager.search(name);
    }

    else if (cmd == "-U")
    {
        if (argc < 3) return;

        std::string target = argv[2];

        if (target == "-A")
        {
            packageManager.updateAll();
            libraryManager.updateAll();
        }
        else if (target == "-pack")
        {
            packageManager.updateAll();
        }
        else if (target == "-lib")
        {
            libraryManager.updateAll();
        }
    }

    else
    {
        std::cout << "Unknown command\n";
    }
}