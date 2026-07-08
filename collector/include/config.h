#ifndef CONFIG_H
#define CONFIG_H

#include <string>

class Config
{
public:

    std::string registryURL;

    std::string dependencyPath;

    std::string cachePath;

    std::string tempPath;

    bool load();

    bool save();
};

#endif