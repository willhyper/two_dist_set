package TwoDistSet.Matrix;

/**
 * Created by chaoweichen on 12/18/13.
 */
public class LogCompleteMatrix {

    private static int count = 0;
    public static void log(MatrixUnit matrix){

        String stringBuffer = ("coined complete matrix no." + count++ + "\n") + matrix.toString();

        System.out.print(stringBuffer);

    }


}
