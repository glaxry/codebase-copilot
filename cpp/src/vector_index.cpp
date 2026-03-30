#include "vector_index.h"

#include <algorithm>
#include <cmath>
#include <queue>
#include <stdexcept>

namespace codebase_copilot {

float VectorIndex::compute_norm(const std::vector<float>& vector) {
    float squared_sum = 0.0f;
    for (float value : vector) {
        squared_sum += value * value;
    }
    return std::sqrt(squared_sum);
}

void VectorIndex::add_item(int id, const std::vector<float>& vector) {
    if (vector.empty()) {
        throw std::invalid_argument("embedding must not be empty");
    }

    if (dimension_ == 0) {
        dimension_ = vector.size();
    } else if (vector.size() != dimension_) {
        throw std::invalid_argument("embedding dimension does not match existing index");
    }

    const float norm = compute_norm(vector);
    if (norm == 0.0f) {
        throw std::invalid_argument("embedding norm must be non-zero");
    }

    entries_.push_back(Entry{id, vector, norm});
}

void VectorIndex::add_items(const std::vector<int>& ids, const std::vector<std::vector<float>>& vectors) {
    if (ids.size() != vectors.size()) {
        throw std::invalid_argument("ids and vectors must have the same length");
    }

    for (std::size_t index = 0; index < ids.size(); ++index) {
        add_item(ids[index], vectors[index]);
    }
}

std::vector<std::pair<int, float>> VectorIndex::search(
    const std::vector<float>& query,
    std::size_t top_k) const {
    if (top_k == 0 || entries_.empty()) {
        return {};
    }

    if (query.size() != dimension_) {
        throw std::invalid_argument("query dimension does not match index dimension");
    }

    const float query_norm = compute_norm(query);
    if (query_norm == 0.0f) {
        throw std::invalid_argument("query norm must be non-zero");
    }

    using HeapItem = std::pair<float, int>;
    const auto compare = [](const HeapItem& left, const HeapItem& right) {
        return left.first > right.first;
    };

    // Keep the current best top-k items in a min-heap so we only store
    // the most relevant scores as we scan the full vector collection.
    std::priority_queue<HeapItem, std::vector<HeapItem>, decltype(compare)> best_items(compare);

    for (const Entry& entry : entries_) {
        float dot_product = 0.0f;
        for (std::size_t index = 0; index < query.size(); ++index) {
            dot_product += query[index] * entry.embedding[index];
        }

        const float score = dot_product / (query_norm * entry.norm);

        if (best_items.size() < top_k) {
            best_items.emplace(score, entry.id);
            continue;
        }

        if (score > best_items.top().first) {
            best_items.pop();
            best_items.emplace(score, entry.id);
        }
    }

    std::vector<std::pair<int, float>> results;
    results.reserve(best_items.size());
    while (!best_items.empty()) {
        const auto [score, id] = best_items.top();
        best_items.pop();
        results.emplace_back(id, score);
    }

    // The heap pops the smallest score first, so reverse to return
    // results from highest similarity to lowest similarity.
    std::reverse(results.begin(), results.end());
    return results;
}

std::size_t VectorIndex::size() const noexcept {
    return entries_.size();
}

std::size_t VectorIndex::dimension() const noexcept {
    return dimension_;
}

}  // namespace codebase_copilot
