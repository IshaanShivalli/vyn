#include "downloader.h"

#include <filesystem>
#include <urlmon.h>

bool Downloader::download(const std::string& url,
                          const std::string& output)
{
    std::filesystem::create_directories(std::filesystem::path(output).parent_path());
    HRESULT hr = URLDownloadToFileA(NULL, url.c_str(), output.c_str(), 0, NULL);
    return SUCCEEDED(hr);
}
