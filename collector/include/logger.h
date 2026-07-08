#ifndef LOGGER_H
#define LOGGER_H

#include <string>

class Logger
{
public:

    static void info(const std::string&);

    static void warning(const std::string&);

    static void error(const std::string&);
};

#endif