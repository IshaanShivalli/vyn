#include "logger.h"

#include <iostream>

void Logger::info(const std::string& msg)
{
    std::cout << "[INFO] " << msg << '\n';
}

void Logger::warning(const std::string& msg)
{
    std::cout << "[WARNING] " << msg << '\n';
}

void Logger::error(const std::string& msg)
{
    std::cout << "[ERROR] " << msg << '\n';
}