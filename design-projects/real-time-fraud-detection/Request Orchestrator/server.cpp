// server.cpp
#include <iostream>
#include <map>
#include <mutex>
#include <string>
#include "httplib.h"
#include "json.hpp"

using json = nlohmann::json;
using namespace httplib;

std::map<int, json> items;
std::mutex items_mtx;
int next_id = 1;

int main()
{
    Server svr;

    svr.Get("/", [](const Request &, Response &res)
            { res.set_content("<h1>C++ API running</h1>", "text/html"); });

    svr.Get("/health", [](const Request &, Response &res)
            { res.set_content(json({{"status", "ok"}}).dump(), "application/json"); });

}
