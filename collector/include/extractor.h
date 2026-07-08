#ifndef EXTRACTOR_H
#define EXTRACTOR_H

#include <string>

class Extractor
{
public:

    bool unzip(
        const std::string& archive,
        const std::string& destination
    );
};

#endif