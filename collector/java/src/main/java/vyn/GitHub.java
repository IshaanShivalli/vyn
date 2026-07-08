package vyn;

public class GitHub {

    public String rawURL(String type,
                         String library,
                         String file) {

        return "https://raw.githubusercontent.com/IshaanShivalli/vyn-lib/main/"
                + type + "/"
                + library + "/"
                + file;

    }

}