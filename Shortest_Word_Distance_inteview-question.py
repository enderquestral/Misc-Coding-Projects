from typing import List


class Solution:
    def shortestDistance(self, wordsDict: List[str], word1: str, word2: str) -> int:
        min_dist = float('inf')
        index1 = index2 = -1

        for i, word in enumerate(wordsDict):
            print(f"Checking word: {word} at index {i}")
            if word == word1:
                index1 = i
                if index2 != -1:
                    min_dist = min(min_dist, abs(index1 - index2))
            elif word == word2:
                index2 = i
                if index1 != -1:
                    min_dist = min(min_dist, abs(index1 - index2))

        return int(min_dist)


# Example usage:
if __name__ == "__main__":
    sol = Solution()
    print(sol.shortestDistance(["practice", "makes", "perfect", "coding", "makes"], "coding", "practice"))
    print(sol.shortestDistance(["practice", "makes", "perfect", "coding", "makes"], "makes", "coding"))
