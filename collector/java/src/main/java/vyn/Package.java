package vyn;

public class Package {

    private String name;

    private String version;

    private String author;

    private String description;

    public Package() {
    }

    public Package(String name,
                   String version,
                   String author,
                   String description) {

        this.name = name;
        this.version = version;
        this.author = author;
        this.description = description;

    }

}