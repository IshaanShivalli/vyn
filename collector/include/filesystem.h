#ifndef FILESYSTEM_H
#define FILESYSTEM_H

#include <string>

class FileSystem
{
public:

    bool createFolder(const std::string&);

    bool removeFolder(const std::string&);

    bool copy(const std::string&, const std::string&);

    bool exists(const std::string&);
};

#endif