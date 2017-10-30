package TwoDistSet.EvolveApproach;

import TwoDistSet.Matrix.LogCompleteMatrix;
import TwoDistSet.Matrix.MatrixOperation;
import TwoDistSet.Matrix.MatrixUnit;

import java.util.Collection;
import java.util.LinkedList;

/**
 * Created with IntelliJ IDEA.
 * User: chaoweichen
 * Date: 12/1/13
 * Time: 3:28 PM
 * To change this template use File | Settings | File Templates.
 */
public class MainSingleThread {
    final private int dimension = 10;
    final private int rowSum = 6;

    //private long processedMatrixNumber = 0;
    private long completed = 0;

    public static void main(String[] args){
        MainSingleThread mainSingleThread = new MainSingleThread();
        mainSingleThread.evolve();
        System.out.println("Program ends");
    }

    private void evolve(){

        Collection<MatrixUnit> derivedMatrix;
        Collection<MatrixUnit> validMatrix;
        Collection<MatrixUnit> completedMatrix;
        LinkedList<MatrixUnit> matrixWaitForProcess = new LinkedList<MatrixUnit>();

        matrixWaitForProcess.add(new MatrixUnit(dimension,rowSum));
        while(!matrixWaitForProcess.isEmpty()){
            MatrixUnit matrix = matrixWaitForProcess.pollLast();
            // processedMatrixNumber++;

            derivedMatrix = MatrixOperation.derive(matrix);
            validMatrix = MatrixOperation.validate(derivedMatrix);
            completedMatrix = MatrixOperation.harvastCompleted(validMatrix);

            validMatrix.removeAll(completedMatrix);
            matrixWaitForProcess.addAll(validMatrix);

            int n = completedMatrix.size();
            if(n>0) {
                completed += n;
                System.out.println(completed);
            }
        }

    }

}
