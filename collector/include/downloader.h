#ifndef DOWNLOADER_H
#define DOWNLOADER_H

#include <string>

class Downloader
{
public:

    bool download(
        const std::string& url,
        const std::string& output
    );
};

#endif