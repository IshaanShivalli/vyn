#ifndef JSON_H
#define JSON_H

#include <string>

class JSON
{
public:

    bool load(
        const std::string& path
    );

    bool save(
        const std::string& path
    );

    std::string value(
        const std::string& key
    );
};

#endif