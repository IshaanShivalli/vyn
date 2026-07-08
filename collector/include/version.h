#ifndef VERSION_H
#define VERSION_H

#include <string>

class Version
{
public:

    static bool newer(
        const std::string& installed,
        const std::string& latest
    );
};

#endif