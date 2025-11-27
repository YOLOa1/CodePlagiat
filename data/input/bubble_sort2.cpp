#include <iostream>
#include <vector>

void sortWithBubble(std::vector<int>& data) {
    int length = data.size();
    
    for (int i = 0; i < length; i++) {
        bool hasSwapped = false;
        
        for (int j = 0; j < length - i - 1; j++) {
            if (data[j] > data[j + 1]) {
                std::swap(data[j], data[j + 1]);
                hasSwapped = true;
            }
        }
        
        if (!hasSwapped) {
            break;
        }
    }
}

int main() {
    std::vector<int> values = {64, 34, 25, 12, 22, 11, 90};
    
    std::cout << "Before sorting: ";
    for (int value : values) {
        std::cout << value << " ";
    }
    std::cout << std::endl;
    
    sortWithBubble(values);
    
    std::cout << "After sorting: ";
    for (int value : values) {
        std::cout << value << " ";
    }
    std::cout << std::endl;
    
    return 0;
}
