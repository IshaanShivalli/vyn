#ifndef UTILS_H
#define UTILS_H

#include <string>

namespace Utils
{
    std::string toLower(const std::string&);

    bool startsWith(
        const std::string&,
        const std::string&
    );
}

#endif