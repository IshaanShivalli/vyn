#include "file.h"

#include <filesystem>
#include <fstream>

namespace fs = std::filesystem;

bool File::createDirectory(
    const std::string& path
)
{
    return fs::create_directories(path);
}

bool File::removeDirectory(
    const std::string& path
)
{
    return fs::remove_all(path);
}

bool File::write(
    const std::string& file,
    const std::string& text
)
{
    std::ofstream out(file);

    if(!out)
        return false;

    out << text;

    out.close();

    return true;
}

bool File::copy(
    const std::string& from,
    const std::string& to
)
{
    fs::copy(
        from,
        to,
        fs::copy_options::recursive |
        fs::copy_options::overwrite_existing
    );

    return true;
}

bool File::exists(
    const std::string& path
)
{
    return fs::exists(path);
}