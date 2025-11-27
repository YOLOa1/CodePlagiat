public class BubbleSort2 {
    // Variante avec des noms différents
    public static void sortArray(int[] array) {
        int length = array.length;
        
        for (int i = 0; i < length; i++) {
            boolean hasSwapped = false;
            
            for (int j = 0; j < length - i - 1; j++) {
                if (array[j] > array[j + 1]) {
                    int temporary = array[j];
                    array[j] = array[j + 1];
                    array[j + 1] = temporary;
                    hasSwapped = true;
                }
            }
            
            if (!hasSwapped) {
                break;
            }
        }
    }
    
    public static void main(String[] args) {
        int[] data = {64, 34, 25, 12, 22, 11, 90};
        
        System.out.print("Before sorting: ");
        for (int value : data) {
            System.out.print(value + " ");
        }
        System.out.println();
        
        sortArray(data);
        
        System.out.print("After sorting: ");
        for (int value : data) {
            System.out.print(value + " ");
        }
        System.out.println();
    }
}
