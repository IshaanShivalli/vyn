#include "version.h"

bool Version::newer(const std::string& installed,
                    const std::string& latest)
{
    return latest > installed;
}