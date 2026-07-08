#ifndef GITHUB_H
#define GITHUB_H

#include <string>

class GitHub
{
public:

    std::string rawURL(
        const std::string& type,
        const std::string& name,
        const std::string& file
    );

    bool exists(
        const std::string& url
    );
};

#endif