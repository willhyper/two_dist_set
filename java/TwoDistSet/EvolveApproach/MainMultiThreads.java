package TwoDistSet.EvolveApproach;

import TwoDistSet.Matrix.LogCompleteMatrix;
import TwoDistSet.Matrix.MatrixBank;
import TwoDistSet.Matrix.MatrixOperation;
import TwoDistSet.Matrix.MatrixUnit;
import java.util.*;

/**
 * Created with IntelliJ IDEA.
 * User: chaoweichen
 * Date: 12/1/13
 * Time: 3:28 PM
 * To change this template use File | Settings | File Templates.
 */
public class MainMultiThreads extends MatrixBank{
    final private Integer dimension;
    final private Integer rowSum;

    private volatile long processedMatrixNumber =0;
    private volatile int collectedCompleteMatrixNumber=0;


    public static void main(String[] args)
    {
        MainMultiThreads.preCheck(args);
        MainMultiThreads main = new MainMultiThreads(args);

        main.evolveUntilDone();
    }


    public MainMultiThreads(String[] args){

        dimension = Integer.parseInt(args[0]);
        rowSum = Integer.parseInt(args[1]);
        addOneMatrixToProcess(new MatrixUnit(dimension,rowSum));


    }
    private synchronized void addOneProcessedMatrixNumber(){
        processedMatrixNumber++;
    }

    private void evolveUntilDone(){
        new Worker().run();
    }

    private class Worker extends Thread {
        @Override
        public void run() {
            while(!isMatrixForProcessEmpty()){
                MatrixUnit matrixForProcess = getOneMatrixForProcess();
                if(matrixForProcess==null)break;
                addOneProcessedMatrixNumber();

                Collection<MatrixUnit> matrixDerived = MatrixOperation.derive(matrixForProcess);
                Collection<MatrixUnit> matrixValidated = MatrixOperation.validate(matrixDerived);
                Collection<MatrixUnit> matrixComplete = MatrixOperation.harvastCompleted(matrixValidated);
                Collection<MatrixUnit> matrixForNextIteration = MatrixOperation.getMatrixInComplete(matrixValidated, matrixComplete);

                addAllMatrixToProcess(matrixForNextIteration);
                logCompleteMatrix(matrixComplete);
            }
        }
    }
    private synchronized void logCompleteMatrix(Collection<MatrixUnit> matrixComplete){
        for(MatrixUnit matrix:matrixComplete){
            LogCompleteMatrix.log(matrix);
        }
    }




    private static void preCheck(String[] args){

        if(args.length!=2){
            System.out.println("required two integer input arguments, such as 10 6");
            System.exit(0);
        }
        else{
            System.out.println(
                    String.format(
                            "TwoDisSet problem (%s,%s) starts...",
                            args[0],args[1]));
        }

    }
}
