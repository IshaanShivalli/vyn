#include "github.h"

std::string GitHub::rawURL(
    const std::string& type,
    const std::string& name,
    const std::string& file
)
{
    return "https://raw.githubusercontent.com/IshaanShivalli/vyn-lib/main/"
        + type + "/"
        + name + "/"
        + file;
}

bool GitHub::exists(const std::string& url)
{
    return true;
}