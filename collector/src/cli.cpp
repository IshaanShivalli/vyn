#include "cli.h"
#include "package_manager.h"
#include "library_manager.h"

#include <iostream>
#include <string>

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