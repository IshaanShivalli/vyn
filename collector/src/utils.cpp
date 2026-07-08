#include "utils.h"

#include <algorithm>

std::string Utils::toLower(const std::string& text)
{
    std::string s = text;

    std::transform(
        s.begin(),
        s.end(),
        s.begin(),
        ::tolower
    );

    return s;
}

bool Utils::startsWith(const std::string& text,
                       const std::string& prefix)
{
    if(prefix.size() > text.size())
        return false;

    return text.compare(0, prefix.size(), prefix) == 0;
}