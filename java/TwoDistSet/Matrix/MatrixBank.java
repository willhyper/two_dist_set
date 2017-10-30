package TwoDistSet.Matrix;

import java.util.Collection;
import java.util.LinkedList;

/**
 * Created by chaoweichen on 12/19/13.
 */
public class MatrixBank {
    private volatile LinkedList<MatrixUnit> matrixForProcess;

    public MatrixBank() {
        matrixForProcess = new LinkedList<MatrixUnit>();
    }

    protected synchronized void addOneMatrixToProcess(MatrixUnit matrix){
        matrixForProcess.add(matrix);
    }

    protected synchronized MatrixUnit getOneMatrixForProcess(){
        return matrixForProcess.pollLast();
    }


    protected synchronized boolean isMatrixForProcessEmpty(){
        return matrixForProcess.isEmpty();
    }

    protected void addAllMatrixToProcess(Collection<MatrixUnit> matricies){
        for(MatrixUnit matrix:matricies)
            addOneMatrixToProcess(matrix);
    }

    protected Collection<MatrixUnit> getNMatrixForProcess(int N){
        N = (N>=matrixForProcess.size())? matrixForProcess.size() : N;
        Collection<MatrixUnit> matrixForProcessCollection = new LinkedList<MatrixUnit>();
        for(int n=0;n<N;n++){
            matrixForProcessCollection.add(getOneMatrixForProcess());
        }
        return matrixForProcessCollection;
    }

}
