#pragma once

#include <cstddef>
#include <utility>
#include <vector>

namespace codebase_copilot {

class VectorIndex {
public:
    void add_item(int id, const std::vector<float>& vector);
    void add_items(const std::vector<int>& ids, const std::vector<std::vector<float>>& vectors);

    std::vector<std::pair<int, float>> search(
        const std::vector<float>& query,
        std::size_t top_k) const;

    std::size_t size() const noexcept;
    std::size_t dimension() const noexcept;

private:
    struct Entry {
        int id;
        std::vector<float> embedding;
        float norm;
    };

    static float compute_norm(const std::vector<float>& vector);

    std::vector<Entry> entries_;
    std::size_t dimension_ = 0;
};

}  // namespace codebase_copilot
