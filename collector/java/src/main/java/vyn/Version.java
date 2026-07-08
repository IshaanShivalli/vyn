package vyn;

public class Version {

    public static boolean newer(String installed,
                                String latest) {

        return latest.compareTo(installed) > 0;

    }

}