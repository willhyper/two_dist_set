package TwoDistSet.Matrix;

import TwoDistSet.Matrix.Exception.RowNotCompleteException;

/**
 * Created with IntelliJ IDEA.
 * User: chaoweichen
 * Date: 12/1/13
 * Time: 12:54 PM
 * To change this template use File | Settings | File Templates.
 */
public class MatrixUnit {
    private Integer[][] matrix;
    private int dim;
    private int rowSumRequired;
    public MatrixUnit(Integer[][] matrix) {
        this.matrix = matrix.clone();

    }

    public MatrixUnit(int dimension, int rowSumRequired) {
        this.dim = dimension;
        this.rowSumRequired = rowSumRequired;
        generateMatrixBackBone();
    }

    public static MatrixUnit getCopy(MatrixUnit matrix) {
        int dimension = matrix.dim;
        Integer[][] matrixContent = new Integer[dimension][dimension];

        for(int r=0;r<dimension;r++)
            for(int c=0;c<dimension;c++)
                matrixContent[r][c]=matrix.matrix[r][c];

        MatrixUnit matrixCopy = new MatrixUnit(matrixContent);
        matrixCopy.dim = dimension;
        matrixCopy.rowSumRequired = matrix.rowSumRequired;
        return matrixCopy;
    }

    private void generateMatrixBackBone(){
        matrix = new Integer[dim][dim];
        for(int r = 0; r< dim; r++)
            for(int c = 0; c< dim; c++)
                matrix[r][c]=null;

        for(int diag = 0; diag< dim; diag++)
            matrix[diag][diag]=0;
    }


    @Override
    public String toString(){
        StringBuilder stringBuffer = new StringBuilder();
        for(int r = 0; r< dim; r++){
            for(int c = 0; c< dim; c++){
                String elementAsString = getMatrixValueAsStringAt(r, c);
                stringBuffer.append(elementAsString + " ");
            }
            stringBuffer.append("\n");
        }
        return stringBuffer.toString();


    }

    private String getMatrixValueAsStringAt(int r, int c)
    {
        return isMatrixValueDeterminedAt(r,c) ? String.valueOf(matrix[r][c]) : "n";
    }

    public void setMatrixValue1At(int r,int c){
        matrix[r][c]=1;
        matrix[c][r]=1;
    }

    public void setMatrixValue0At(int r,int c){
        matrix[r][c]=0;
        matrix[c][r]=0;
    }

    private int getRowSumAtRow(int r) throws RowNotCompleteException {
        if(!isRowComplete(r))
            throw new RowNotCompleteException();

        int sum=0;
        for(int c = 0; c< dim; c++){
            if(isMatrixValueDeterminedAt(r,c))
               sum += matrix[r][c];
        }
        return sum;
    }


    private int getInnerProductAt(int r1,int r2) throws RowNotCompleteException{
        if(!isRowComplete(r1)) throw new RowNotCompleteException();
        if(!isRowComplete(r2)) throw new RowNotCompleteException();
        int innerProduct = 0;
        for(int c = 0; c< dim; c++){
            innerProduct += matrix[r1][c]*matrix[r2][c];
        }
        return innerProduct;
    }


    public int[] getNextUndeterminedCoordinate(){
        for(int r = 0; r< dim; r++){
            for(int c = 0; c< dim; c++){
                if(!isMatrixValueDeterminedAt(r,c))
                    return new int[]{r,c};
            }
        }

        return null;
    }


    public boolean isMatrixComplete(){
        for(int r = 0; r< dim; r++)
            if(!isRowComplete(r))
                return false;
        return true;
    }

    public boolean isRowComplete(int r){
        for(int c = 0; c< dim; c++)
            if(!isMatrixValueDeterminedAt(r,c))
                return false;
        return true;
    }

    private boolean isMatrixValueDeterminedAt(int r,int c){
        return matrix[r][c]!=null;
    }
    public boolean isCurrentlyValid() {

        for(int r = 0; r< dim; r++){
            if(!isSatisfyCondition3(r)){
                return false;
            }

        }

        for(int r1 = 0; r1< dim; r1++){
            for(int r2 = r1+1; r2< dim; r2++){
                if(!isSatisfyCondition5(r1,r2)){
                    return false;
                }

            }
        }

        return true;

    }

    private boolean isSatisfyCondition3(int r){
        try {
            int rowSum = getRowSumAtRow(r);
            return rowSum<=rowSumRequired;
        } catch (RowNotCompleteException e) {
            return true;
        }


    }
    private boolean isSatisfyCondition5(int r1,int r2){
        //sum(A(i,:).*A(j,:))=  4-A(i,j) , i!=j
        try {
            int innerProduct = getInnerProductAt(r1,r2);
            return innerProduct==4-matrix[r1][r2];
        } catch (RowNotCompleteException e) {
            return true;
        }
    }

}
