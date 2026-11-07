from typing import List


class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        if not intervals:
            return []

        intervals.sort(key=lambda x: (x[0], x[1]))
        merged = [intervals[0]]

        for start, end in intervals[1:]:
            last_start, last_end = merged[-1]

            if start <= last_end:
                merged[-1][1] = max(last_end, end)
            else:
                merged.append([start, end])

        return merged


# Example usage:
if __name__ == "__main__":
    sol = Solution()
    print(sol.merge([[1, 3], [2, 6], [8, 10], [15, 18]]))
    print(sol.merge([[1, 4], [4, 5]]))
