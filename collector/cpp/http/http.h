#ifndef HTTP_H
#define HTTP_H

#include <string>

class HTTP
{
public:

    bool download(
        const std::string& url,
        const std::string& output
    );

    std::string get(
        const std::string& url
    );
};

#endif