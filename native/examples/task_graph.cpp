/** Standalone C++17 consumer of the unchanged C11 ABI.
 * Inputs: task_graph.ndjson, a new cell-output filename.
 * Outputs: owned canonical cell bytes and complete native metadata on stdout.
 * Errors: nonzero exit with a diagnostic; no provider, terminal or subprocess use.
 * Example: task-graph native/examples/task_graph.ndjson /tmp/graph.cells
 */
#include "nocturne_native.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

/** Align and own the C context. Commands and rendering remain C-authoritative. */
class NativeOwner {
    std::vector<std::uint64_t> storage;
public:
    NativeOwner() : storage((static_cast<std::size_t>(nrContextSize())+7)/8) {
        if (nrInit(storage.data(),nrContextSize(),2030)!=0)
            throw std::runtime_error("native initialization failed");
    }
    NrContext* context() { return reinterpret_cast<NrContext*>(storage.data()); }
    void command(const std::string& value) {
        if (value.size()>65536) throw std::runtime_error("command exceeds C ABI bound");
        int result=nrCommand(context(),value.data(),static_cast<std::uint32_t>(value.size()));
        if (result<0) throw std::runtime_error(nrError(context()));
        if (result==1) throw std::runtime_error("unexpected pending catch-up in fixed graph fixture");
    }
};

int main(int argc,char** argv) {
    try {
        if (argc!=3) throw std::runtime_error("usage: task-graph INPUT.ndjson NEW_OUTPUT.cells");
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open commands");
        if (std::ifstream(argv[2]).good()) throw std::runtime_error("output exists; refusing overwrite");
        NativeOwner scene;
        std::string line;std::size_t count=0;
        while (std::getline(input,line)) {
            if (++count>256) throw std::runtime_error("graph command count bound exceeded");
            if (!line.empty()) scene.command(line);
        }
        scene.command(R"({"op":"time","timeUs":900000})");
        const auto countCells=nrRender(scene.context());
        if (!countCells) throw std::runtime_error("native render failed");
        const auto* first=reinterpret_cast<const char*>(nrCells(scene.context()));
        std::vector<char> owned(first,first+static_cast<std::size_t>(countCells)*16);
        std::ofstream output(argv[2],std::ios::binary);
        if (!output.write(owned.data(),static_cast<std::streamsize>(owned.size())))
            throw std::runtime_error("cell output failed");
        std::cout<<nrInfo(scene.context())<<'\n';
        return 0;
    } catch(const std::exception& error) {
        std::cerr<<error.what()<<'\n';return 1;
    }
}
