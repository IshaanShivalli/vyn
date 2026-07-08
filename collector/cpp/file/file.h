#ifndef FILE_H
#define FILE_H

#include <string>

class File
{
public:

    bool createDirectory(
        const std::string& path
    );

    bool removeDirectory(
        const std::string& path
    );

    bool write(
        const std::string& file,
        const std::string& text
    );

    bool copy(
        const std::string& from,
        const std::string& to
    );

    bool exists(
        const std::string& path
    );
};

#endif