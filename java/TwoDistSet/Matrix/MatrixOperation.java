package TwoDistSet.Matrix;

import java.util.ArrayList;
import java.util.Collection;

/**
 * Created by chaoweichen on 12/18/13.
 */
public class MatrixOperation {

    public static Collection<MatrixUnit> derive(Collection<MatrixUnit> matricies){
        Collection<MatrixUnit> derivedMatrix = new ArrayList<MatrixUnit>();
        for(MatrixUnit matrix: matricies){
            derivedMatrix.addAll(derive(matrix));
        }
        return derivedMatrix;
    }

    public static Collection<MatrixUnit> derive(MatrixUnit matrix) {
        Collection<MatrixUnit> newMatrixList = new ArrayList<MatrixUnit>();
        if (matrix.isMatrixComplete()) {
            return newMatrixList;
        } else {
            int[] undeterminedCoordinate = matrix.getNextUndeterminedCoordinate();

            MatrixUnit newMatrix0 = MatrixUnit.getCopy(matrix);
            newMatrix0.setMatrixValue0At
                    (undeterminedCoordinate[0], undeterminedCoordinate[1]);
            MatrixUnit newMatrix1 = MatrixUnit.getCopy(matrix);
            newMatrix1.setMatrixValue1At
                    (undeterminedCoordinate[0], undeterminedCoordinate[1]);

            newMatrixList.add(newMatrix0);
            newMatrixList.add(newMatrix1);
        }
        return newMatrixList;
    }

    public static Collection<MatrixUnit> validate(Collection<MatrixUnit> matrices){
        Collection<MatrixUnit> validMatrices = new ArrayList<MatrixUnit>();
        for(MatrixUnit matrix: matrices){
            MatrixUnit validatedMatrix =returnValidOrNull(matrix);
            if(validatedMatrix!=null)
                validMatrices.add(validatedMatrix);
        }

        return validMatrices;
    }
    public static MatrixUnit returnValidOrNull(MatrixUnit matrix) {
        if (matrix.isCurrentlyValid())
            return matrix;
        else
            return null;
    }


    public static Collection<MatrixUnit> harvastCompleted(Collection<MatrixUnit> matricies){
        Collection<MatrixUnit> matrixComplete = new ArrayList<MatrixUnit>();
        for(MatrixUnit matrix:matricies){
                if(matrix.isMatrixComplete())
                    matrixComplete.add(matrix);

        }
        return matrixComplete;
    }


    public static Collection<MatrixUnit> getMatrixInComplete(Collection<MatrixUnit> validMatrix, Collection<MatrixUnit> matrixComplete){
        Collection<MatrixUnit> matrixInComplete = new ArrayList<MatrixUnit>();
        matrixInComplete.addAll(validMatrix);
        matrixInComplete.removeAll(matrixComplete);
        return matrixInComplete;
    }
}
