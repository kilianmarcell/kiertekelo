import java.util.*;
public class SomeList<T> extends ArrayList<T> {
    public SomeList() { super(); }
    public SomeList(Collection<? extends T> c) { super(c); }
    public void putAll(Collection<? extends T> c) { this.addAll(c); }
    public void shuffle() { Collections.shuffle(this); }
}
